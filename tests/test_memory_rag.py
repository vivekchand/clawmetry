"""Tests for /api/memory-rag and /api/memory-rag/search (issue #610).

Creates a minimal in-process SQLite database with the expected schema
(files, chunks, chunks_fts FTS5), mounts it as the RAG store, and
exercises the two bp_memory routes without spinning up a real server.
"""

from __future__ import annotations

import importlib
import os
import sqlite3

import pytest
from flask import Flask


# ── helpers ────────────────────────────────────────────────────────────────


def _make_rag_db(path: str) -> None:
    """Create a minimal main.sqlite with files + chunks + FTS5 table."""
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE files (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            path  TEXT NOT NULL,
            size  INTEGER DEFAULT 0,
            mtime INTEGER DEFAULT 0
        );
        CREATE TABLE chunks (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            content TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            content,
            content=chunks,
            content_rowid=id
        );
        CREATE TRIGGER chunks_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, content) VALUES (new.id, new.content);
        END;
        """
    )
    conn.execute("INSERT INTO files (path, size, mtime) VALUES (?, ?, ?)",
                 ("notes/project.md", 1024, 1700000000))
    conn.execute("INSERT INTO files (path, size, mtime) VALUES (?, ?, ?)",
                 ("notes/archive.md", 512, 1699000000))
    file_id_1 = conn.execute("SELECT id FROM files WHERE path='notes/project.md'").fetchone()[0]
    file_id_2 = conn.execute("SELECT id FROM files WHERE path='notes/archive.md'").fetchone()[0]
    conn.execute("INSERT INTO chunks (file_id, content) VALUES (?, ?)",
                 (file_id_1, "The project uses Python and Flask for the backend."))
    conn.execute("INSERT INTO chunks (file_id, content) VALUES (?, ?)",
                 (file_id_1, "Frontend is embedded HTML with no build step required."))
    conn.execute("INSERT INTO chunks (file_id, content) VALUES (?, ?)",
                 (file_id_2, "Archived notes about the old architecture."))
    conn.commit()
    conn.close()


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask test app with bp_memory, pointing MEMORY_DIR at a temp dir
    that contains a fully-populated main.sqlite."""
    db_path = tmp_path / "main.sqlite"
    _make_rag_db(str(db_path))

    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    import dashboard as _d
    monkeypatch.setattr(_d, "MEMORY_DIR", str(tmp_path), raising=False)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_memory)
    return a


@pytest.fixture
def app_no_db(tmp_path, monkeypatch):
    """Flask test app where main.sqlite does NOT exist."""
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    import dashboard as _d
    monkeypatch.setattr(_d, "MEMORY_DIR", str(tmp_path), raising=False)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_memory)
    return a


# ── /api/memory-rag ────────────────────────────────────────────────────────


def test_memory_rag_available(app):
    with app.test_client() as c:
        r = c.get("/api/memory-rag")
    assert r.status_code == 200
    data = r.get_json()
    assert data["available"] is True
    assert data["stats"]["fileCount"] == 2
    assert data["stats"]["chunkCount"] == 3
    assert data["stats"]["totalBytes"] == 1024 + 512


def test_memory_rag_files_sorted_by_size(app):
    with app.test_client() as c:
        data = c.get("/api/memory-rag").get_json()
    files = data["files"]
    assert len(files) == 2
    assert files[0]["path"] == "notes/project.md"
    assert files[0]["size"] == 1024
    assert files[0]["chunkCount"] == 2
    assert files[1]["path"] == "notes/archive.md"
    assert files[1]["chunkCount"] == 1


def test_memory_rag_last_indexed(app):
    with app.test_client() as c:
        data = c.get("/api/memory-rag").get_json()
    assert data["stats"]["lastIndexed"] == 1700000000


def test_memory_rag_unavailable_when_no_db(app_no_db):
    with app_no_db.test_client() as c:
        r = c.get("/api/memory-rag")
    assert r.status_code == 200
    data = r.get_json()
    assert data["available"] is False
    assert data["files"] == []


# ── /api/memory-rag/search ─────────────────────────────────────────────────


def test_memory_rag_search_hit(app):
    with app.test_client() as c:
        r = c.get("/api/memory-rag/search?q=Python")
    assert r.status_code == 200
    data = r.get_json()
    assert data["available"] is True
    assert data["total"] >= 1
    paths = [res["path"] for res in data["results"]]
    assert "notes/project.md" in paths
    snippets = [res["snippet"] for res in data["results"]]
    assert any("Python" in s or "<mark>" in s for s in snippets)


def test_memory_rag_search_no_results(app):
    with app.test_client() as c:
        data = c.get("/api/memory-rag/search?q=xyzzy_nonexistent_token").get_json()
    assert data["available"] is True
    assert data["total"] == 0
    assert data["results"] == []


def test_memory_rag_search_empty_query(app):
    with app.test_client() as c:
        data = c.get("/api/memory-rag/search").get_json()
    assert data["total"] == 0
    assert data["results"] == []


def test_memory_rag_search_unavailable_when_no_db(app_no_db):
    with app_no_db.test_client() as c:
        data = c.get("/api/memory-rag/search?q=anything").get_json()
    assert data["available"] is False


def test_memory_rag_search_limit(app):
    with app.test_client() as c:
        data = c.get("/api/memory-rag/search?q=notes&limit=1").get_json()
    assert len(data["results"]) <= 1
